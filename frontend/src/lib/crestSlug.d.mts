/** See crestSlug.mjs. Declared so the .tsx side stays typed. */
export declare const CLUB_ALIASES: Record<string, string>;
/** The one name a club is known by, whichever dataset supplied it. */
export declare function canonicalClub(club: string): string;
/** Canonical club name -> crest filename stem. */
export declare function crestSlug(club: string): string;
