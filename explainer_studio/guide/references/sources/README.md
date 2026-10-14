# Sources

Two labels describe what a source looks like. Note both in the research notes when you start reading.

- **Kind:** what sort of thing it is. It decides how to read it, where its questions usually hide, and how to quote it
  in the video.
- **File format:** what file it comes in. It decides which tool gets the content out.

Neither decides how many episodes there are or what each answers: that is the plan, which looks at the viewer and the
question map ([teaching/plan.md](../teaching/plan.md)). The other two labels are the subject ([subjects/](../subjects/))
and each episode's question type ([teaching/question-types.md](../teaching/question-types.md)).

## Kinds

Similar kinds share one source reference.

| Kind | id | What it is | Source reference |
|---|---|---|---|
| Essay | `essay` | An article, a report, a blog post; the content of a talk or a lecture | [book-chapter.md](book-chapter.md) |
| Notes and slides | `notes` | A teacher's outline, slides | [book-chapter.md](book-chapter.md) |
| Popular book | `popular` | One big idea, written for general readers | [book-chapter.md](book-chapter.md) |
| Textbook | `textbook` | Many concepts stacked one on another | [book-chapter.md](book-chapter.md) |
| Survey | `survey` | Many topics side by side: a multi-volume set, a general history, a handbook, an encyclopedia | [book-chapter.md](book-chapter.md) |
| Monograph | `monograph` | One specialized argument, densely cited | [book-chapter.md](book-chapter.md) |
| Paper | `paper` | One piece of research | [paper.md](paper.md) |
| Primary source | `primary` | The original author's own words: classics, historical documents, letters | [book-chapter.md](book-chapter.md) |
| Manual | `manual` | Teaches how to do one thing | [book-chapter.md](book-chapter.md) |
| Literature | `literature` | Novels, poems, plays | [book-chapter.md](book-chapter.md) |
| Codebase | `codebase` | A software project | [codebase.md](codebase.md) |
| Code change | `change` | A PR, a series of commits, a diff | [codebase.md](codebase.md) |
| Technical document | `spec` | A design document, a specification, an RFC, API documentation | [codebase.md](codebase.md) |
| Rules and texts of law | `rules` | Laws, contracts, policies, standards | [book-chapter.md](book-chapter.md) |
| Case | `case` | A business, medical or legal case | [book-chapter.md](book-chapter.md) |
| Data | `data` | Datasets, spreadsheets, logs | none yet |
| Conversation | `conversation` | Interviews, dialogues, podcasts, meetings, discussion threads | [book-chapter.md](book-chapter.md) |

- A recording of a talk is an essay (one person, one main line). It must first become a transcript, which is a matter
  of file format.
- A source has one kind. When unsure, pick the kind whose questions it most resembles.
- Data (`data`) has no source reference yet. Draw the question map from the questions the data can answer, say in the
  video what the data cannot show, and record a gap with `explainer-studio gap add --kind other`.

## File formats

| File format | id | How to get the content out | Supported now |
|---|---|---|---|
| PDF, Word or web page with text | `text` | Extract the text directly (for a PDF, any text extractor, for example `pdftotext -layout`) | yes |
| Scans, photos | `scan` | Read the pages as images, one by one (`explainer-studio asset pdf crop <pdf> --page <n>` renders a page) | yes (slower) |
| Audio, video recordings | `audio` | Transcribe first | no |
| Code repository (git) | `repo` | Read the code and its history | yes |
| PR, commits | `diff` | Read the diff and the discussion | no |
| Tables, data files | `table` | Read them as tables | no |
| Slide files | `slides` | Extract each slide's text and pictures | no |

For a format that is not supported: use the closest method (for example ask the user for a transcript, or export to
PDF), and record a gap with `explainer-studio gap add --kind tool`.
