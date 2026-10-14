# Bell Laundry & Cleaners — staging site

Static site for Bell Laundry & Cleaners, deployed to SiteGround (staging16.cleaner.marketing) on every push to `main`.

- Edit pages in `_src/pages/*.html`, the shared header/footer in `_src/layout.html`, icons in `_src/icons.svg`.
- Styles: `assets/css/site.css`. Motion and interactions: `assets/js/site.js` (no dependencies).
- Build: `python -X utf8 _src/build.py` writes `index.html`, `about-us/index.html`, and the other pages. Commit the output.
- `_src/` is not uploaded. The deploy only adds or updates files; it never deletes files on the server.
- Forms (contact, work with us) are preview-only and not connected to a mailbox yet.
- `robots.txt` and the `noindex` meta keep this staging copy out of search results.
