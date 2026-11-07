// Node's built-in TypeScript stripping resolves specifiers literally, so cast.ts's extensionless `./toon` imports
// (which every bundler in this repo handles) throw ERR_MODULE_NOT_FOUND. This hook adds the .ts extension back for
// relative specifiers, which is what lets scripts/is_cast.mjs import the real browser module headlessly.
export async function resolve(specifier, context, next) {
  if (specifier.startsWith(".") && !/\.[a-zA-Z]+$/.test(specifier)) {
    try { return await next(specifier + ".ts", context); } catch { /* fall through */ }
  }
  return next(specifier, context);
}
