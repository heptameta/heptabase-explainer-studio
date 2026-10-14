"""Molecules: skeletal formulas from SMILES with correct geometry (RDKit computes the 2D layout), drawn as native
shapes so atoms, bonds and functional groups can be highlighted and mechanisms drawn with curly arrows.

    ethanol = get_molecule("CCO")
    aspirin = get_molecule("CC(=O)Oc1ccccc1C(=O)O", bond_length=0.7)
    self.play(aspirin.highlight(aspirin.list_matches("C(=O)[OH]")[0], YELLOW))
    arrow = get_mechanism_arrow(nucleophile, ("atom", 0), substrate, ("atom", 1))
    reaction = get_reaction(["CCBr", "[OH-]"], ["CCO", "[Br-]"])
"""

from __future__ import annotations

from manimlib import *

from ..parts import KeyedGroup, Parts
from ..style import LABEL_FONT_SIZE
from .diagrams import get_curved_arrow

__all__ = ["COLOR_BY_ATOM_SYMBOL_MAP", "Molecule", "get_mechanism_arrow", "get_molecule", "get_reaction"]

COLOR_BY_ATOM_SYMBOL_MAP = {"O": RED_C, "N": BLUE_C, "S": YELLOW_D, "P": ORANGE, "F": GREEN_C, "Cl": GREEN_C,
                            "Br": MAROON_C, "I": PURPLE_C, "C": WHITE, "H": WHITE}
_SUBSCRIPT_BY_DIGIT_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


class Molecule(Parts):
    """Parts: .atoms[i] (label, or an invisible point for implicit carbons), .bonds[i] (VGroup of strokes),
    .get_atom_point(i), .get_bond_point(j), .list_matches(smarts) → [(atom indices)], .highlight(indices) →
    animation, .rdmol (the RDKit molecule)."""

    def __init__(self, smiles: str, bond_length: float = 0.75, font_size: float = LABEL_FONT_SIZE - 6,
                 should_color_atoms: bool = True, should_show_carbons: bool = False, stroke_width: float = 3.5,
                 has_explicit_hydrogens: bool = False):
        from rdkit import Chem  # imported here: RDKit is slow to load and most scenes draw no molecule
        from rdkit.Chem import rdDepictor
        super().__init__()
        rdkit_molecule = Chem.MolFromSmiles(smiles)
        if rdkit_molecule is None:
            raise ValueError(f"RDKit could not read SMILES {smiles!r}")
        if has_explicit_hydrogens:
            rdkit_molecule = Chem.AddHs(rdkit_molecule)
        rdDepictor.SetPreferCoordGen(True)
        rdDepictor.Compute2DCoords(rdkit_molecule)
        Chem.WedgeMolBonds(rdkit_molecule, rdkit_molecule.GetConformer())
        Chem.Kekulize(rdkit_molecule, clearAromaticFlags=False)
        self.rdmol, self.smiles = rdkit_molecule, smiles
        conformer = rdkit_molecule.GetConformer()
        raw_positions = np.array([[conformer.GetAtomPosition(i).x, conformer.GetAtomPosition(i).y, 0]
                                  for i in range(rdkit_molecule.GetNumAtoms())])
        bond_lengths = [np.linalg.norm(raw_positions[bond.GetBeginAtomIdx()] - raw_positions[bond.GetEndAtomIdx()])
                        for bond in rdkit_molecule.GetBonds()]
        scale = bond_length / (np.median(bond_lengths) if bond_lengths else 1.5)
        positions = (raw_positions - raw_positions.mean(axis=0)) * scale
        self._positions = positions
        self._stroke_width = stroke_width
        ring_info = rdkit_molecule.GetRingInfo()

        atoms, labeled_atom_indices = [], set()
        is_small = rdkit_molecule.GetNumHeavyAtoms() <= 2          # CH3–Br, H2O: chemists write every carbon out
        for atom in rdkit_molecule.GetAtoms():
            i, symbol = atom.GetIdx(), atom.GetSymbol()
            should_show_label = (symbol != "C" or should_show_carbons or is_small or atom.GetDegree() == 0
                                 or atom.GetFormalCharge() != 0)
            if should_show_label:
                hydrogen_count = atom.GetTotalNumHs()
                if hydrogen_count > 1:
                    hydrogen_text = f"H{hydrogen_count}".translate(_SUBSCRIPT_BY_DIGIT_MAP)
                else:
                    hydrogen_text = "H" if hydrogen_count == 1 else ""
                charge = atom.GetFormalCharge()
                sign = "⁺" if charge > 0 else "⁻"
                charge_text = "" if not charge else (sign if abs(charge) == 1 else f"{abs(charge)}{sign}")
                neighbor_indices = [neighbor.GetIdx() for neighbor in atom.GetNeighbors()]
                # a terminal atom bonded from the right is written H3C– / HO–, so the bond still meets the element
                should_flip = (bool(hydrogen_text) and len(neighbor_indices) == 1
                               and positions[neighbor_indices[0]][0] > positions[i][0] + 1e-3)
                text = (hydrogen_text + symbol if should_flip else symbol + hydrogen_text) + charge_text
                label = Text(text, font_size=font_size)
                label.set_color(COLOR_BY_ATOM_SYMBOL_MAP.get(symbol, WHITE) if should_color_atoms else WHITE)
                symbol_start = len(hydrogen_text) if should_flip else 0            # glyphs of the element symbol itself
                anchor = VGroup(*label[symbol_start:symbol_start + len(symbol)])
                label.shift(positions[i] - anchor.get_center())
                # remember where the element letter sits inside the label (glyph references do not follow moves)
                label._anchor_offset_and_height = (positions[i] - label.get_center(), label.get_height())
                atoms.append(label)
                labeled_atom_indices.add(i)
            else:
                atoms.append(Dot(positions[i], radius=0.001).set_opacity(0))
        bond_clearance = font_size / 48 * 0.24

        bonds = []
        for bond in rdkit_molecule.GetBonds():
            i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            start, end = positions[i].copy(), positions[j].copy()
            delta = end - start
            unit = delta / (np.linalg.norm(delta) or 1)
            if i in labeled_atom_indices:
                start = start + unit * bond_clearance
            if j in labeled_atom_indices:
                end = end - unit * bond_clearance
            normal = np.array([-unit[1], unit[0], 0])
            bond_type = bond.GetBondType()
            strokes = VGroup()
            if bond_type == Chem.BondType.TRIPLE:
                for offset in (-1, 0, 1):
                    strokes.add(Line(start + normal * 0.08 * offset, end + normal * 0.08 * offset))
            elif bond_type == Chem.BondType.DOUBLE:
                rings = [ring for ring in ring_info.AtomRings() if i in ring and j in ring]
                if rings:   # inner second line toward the ring centre, shortened
                    ring_center = positions[list(rings[0])].mean(axis=0)
                    side = 1 if np.dot(ring_center - (start + end) / 2, normal) > 0 else -1
                    strokes.add(Line(start, end))
                    strokes.add(Line(start + unit * 0.14 * bond_length + normal * side * 0.13,
                                     end - unit * 0.14 * bond_length + normal * side * 0.13))
                else:
                    strokes.add(Line(start + normal * 0.055, end + normal * 0.055),
                                Line(start - normal * 0.055, end - normal * 0.055))
            else:
                bond_direction = bond.GetBondDir()
                if bond_direction == Chem.BondDir.BEGINWEDGE:
                    wedge = (Polygon(start, end + normal * 0.09, end - normal * 0.09).set_fill(WHITE, 1)
                             .set_stroke(WHITE, 1))
                    strokes.add(wedge)
                elif bond_direction == Chem.BondDir.BEGINDASH:
                    for fraction in np.linspace(0.1, 1.0, 7):
                        point = start + (end - start) * fraction
                        strokes.add(Line(point + normal * 0.09 * fraction, point - normal * 0.09 * fraction))
                else:
                    strokes.add(Line(start, end))
            strokes.set_stroke(WHITE, stroke_width)
            bonds.append(strokes)
        self.atoms = KeyedGroup({i: atom_mobject for i, atom_mobject in enumerate(atoms)})
        self.bonds = KeyedGroup({i: bond_mobject for i, bond_mobject in enumerate(bonds)})
        self.add(self.bonds, self.atoms)

    def get_atom_point(self, i: int) -> np.ndarray:
        atom = self.atoms[i]
        if hasattr(atom, "_anchor_offset_and_height"):
            offset, built_height = atom._anchor_offset_and_height
            return atom.get_center() + offset * (atom.get_height() / built_height if built_height else 1)
        return atom.get_center()

    def get_bond_point(self, j: int) -> np.ndarray:
        return self.bonds[j].get_center()

    def list_matches(self, smarts: str) -> list[tuple[int, ...]]:
        """Atom indices of every occurrence of a SMARTS pattern (a functional group: C(=O)O, [OH], c1ccccc1 …)."""
        from rdkit import Chem
        pattern = Chem.MolFromSmarts(smarts)
        if pattern is None:
            raise ValueError(f"bad SMARTS {smarts!r}")
        return list(self.rdmol.GetSubstructMatches(pattern))

    def get_parts_for(self, atom_indices) -> VGroup:
        """The atoms plus the bonds between them."""
        atom_index_set = set(atom_indices)
        bonds = [self.bonds[bond.GetIdx()] for bond in self.rdmol.GetBonds()
                 if bond.GetBeginAtomIdx() in atom_index_set and bond.GetEndAtomIdx() in atom_index_set]
        return VGroup(*[self.atoms[i] for i in atom_index_set], *bonds)

    def highlight(self, atom_indices, color=YELLOW) -> Animation:
        """Colour a group of atoms and the bonds between them."""
        parts = self.get_parts_for(atom_indices)
        return parts.animate.set_color(color)


def get_molecule(smiles: str, **kwargs) -> Molecule:
    """Same as Molecule(smiles, **kwargs); see its docstring."""
    return Molecule(smiles, **kwargs)


def get_mechanism_arrow(source: Molecule, source_part: tuple[str, int], target: Molecule,
                        target_part: tuple[str, int], angle: float = -PI / 2.5, color=YELLOW,
                        stroke_width: float = 3) -> VGroup:
    """A curly arrow for a reaction mechanism: from an atom (lone pair) or bond (its electrons) to an atom or bond.
    Parts ("atom", i) / ("bond", j). ShowCreation(arrow.arc) then FadeIn(arrow.tip)."""
    def get_part_point(molecule, part):
        part_kind, index = part
        return molecule.get_atom_point(index) if part_kind == "atom" else molecule.get_bond_point(index)
    start, end = get_part_point(source, source_part), get_part_point(target, target_part)
    direction = (end - start) / (np.linalg.norm(end - start) or 1)
    bulge = np.array([-direction[1], direction[0], 0]) * (1 if angle < 0 else -1)   # the side the arc bows towards
    compute_offset = lambda part: 0.28 if part[0] == "atom" else 0.12            # land beside a label, not on it
    return get_curved_arrow(start + bulge * compute_offset(source_part), end + bulge * compute_offset(target_part),
                            angle=angle, color=color, stroke_width=stroke_width)


def get_reaction(left_smiles: list[str], right_smiles: list[str], label: str = "", bond_length: float = 0.6,
                 spacing: float = 0.45, font_size: float = LABEL_FONT_SIZE) -> VGroup:
    """Reactants → products in one row. Parts: .left[i], .right[i] (Molecules), .arrow, .label."""
    reactants = [Molecule(smiles, bond_length=bond_length) for smiles in left_smiles]
    products = [Molecule(smiles, bond_length=bond_length) for smiles in right_smiles]
    get_plus_sign = lambda: Text("+", font_size=font_size).set_color(GREY_B)
    row = []
    for index, molecule in enumerate(reactants):
        row += ([get_plus_sign()] if index else []) + [molecule]
    arrow = Arrow(ORIGIN, 1.6 * RIGHT, buff=0, fill_color=GREY_B)
    row.append(arrow)
    for index, molecule in enumerate(products):
        row += ([get_plus_sign()] if index else []) + [molecule]
    reaction = Parts(*row).arrange(RIGHT, buff=spacing)
    label_mobject = (Text(label, font_size=font_size - 10).set_color(GREY_A).next_to(arrow, UP, 0.1) if label
                     else VGroup())
    reaction.add(label_mobject)
    reaction.left, reaction.right, reaction.arrow, reaction.label = reactants, products, arrow, label_mobject
    return reaction
