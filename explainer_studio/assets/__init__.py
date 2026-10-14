"""The asset commands: find and fetch external material (Wikimedia Commons, Bioicons, Wikipedia portraits, Our World
in Data, the World Bank), look at PDFs and images, and make clips with Blender and Playwright.

Downloads go to production/shared/assets/<kind>/ unless `--to` says otherwise, and each one is recorded in
production/credits.yaml. Search results keep only free licences; nothing else is blocked by licence.
"""
