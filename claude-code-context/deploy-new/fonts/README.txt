Licensed brand fonts go here, then upload to /var/www/drivetimes/fonts/ on
bbmr-drivetimes-prod. The @font-face rules in index.html already point at these
exact filenames, so no code change is needed — drop the files in and reload.

Preferred format is .woff2. If Marketing supplies desktop fonts instead, .otf
also works (both are listed as sources). Convert .ttf to one of these.

  gelica-semibold.woff2          Gelica 600   headings, route names, "mins"
  gelica-bold.woff2              Gelica 700   traffic status pill
  proximanova-medium.woff2       Proxima 500  "Last updated", schedule note
  proximanova-semibold.woff2     Proxima 600  "Typical: N minutes"
  proximanova-bold.woff2         Proxima 700  clock, the big drive-time number
  proximanova-extrabold.woff2    Proxima 800  date line

Any file that is missing simply falls back to Bitter / Montserrat, so a partial
drop is safe — the sign keeps working, it just won't be brand-exact.

After uploading, confirm each returns HTTP 200:
  curl -I http://44.244.49.134/fonts/gelica-semibold.woff2
