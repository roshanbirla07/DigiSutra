// Original vector portraits: stable, random-looking defaults without network or storage.
// Usernames are available on both account sessions and public product bylines.
export function renderAvatar(profile = {}, className = "avatar") {
  const identity = String(profile.username || profile.uuid || profile.id || "guest");
  let seed = 2166136261;
  for (const character of identity) {
    seed = Math.imul(seed ^ character.codePointAt(0), 16777619) >>> 0;
  }
  const hue = seed % 360;
  const hair = [
    '<path d="M22 34c-2-19 36-24 36 0v7h-6V30c-9 5-15 4-24 2v9h-6z"/>',
    '<path d="M21 34c-4-8 1-15 7-15 2-9 13-10 18-4 10-3 18 8 12 19l-7-7-22 3-7 11z"/>',
    '<path d="M22 35c0-29 36-29 36 0v19l-8-3V29c-12 5-13-7-20 5v17l-8 3z"/>',
    '<path d="M22 34c1-19 35-21 36 0l-7-6-22 2-7 11z"/>',
    '<path d="M22 34c-4-14 6-23 18-22 16-2 23 11 18 22l-6-8c-9 4-14-7-22 4l-8 11z"/>',
  ];
  const glasses = seed & 8
    ? '<g fill="none" stroke-width="1.5"><rect x="28" y="34" width="10" height="8" rx="3"/><rect x="42" y="34" width="10" height="8" rx="3"/><path d="M38 37h4"/></g>' : "";
  const classes = className === "profile-avatar" ? "profile-avatar" : className === "creator-avatar" ? "creator-avatar" : "avatar";
  return `<span class="${classes} illustrated-avatar"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" aria-hidden="true" focusable="false">
    <rect width="80" height="80" fill="hsl(${hue} 42% 90%)"/>
    <circle cx="65" cy="17" r="18" fill="hsl(${hue} 42% 84%)"/>
    <path d="M9 80c0-30 62-30 62 0" fill="hsl(${hue} 42% 36%)"/>
    <path d="M33 49h14v13c-4 5-10 5-14 0z" fill="hsl(${(seed >>> 8) % 35 + 15} 45% 72%)"/>
    <rect x="24" y="19" width="32" height="36" rx="15" fill="hsl(${(seed >>> 8) % 35 + 15} 50% 81%)"/>
    <g fill="hsl(${hue} 24% 20%)">${hair[(seed >>> 4) % hair.length]}</g>
    <g stroke="hsl(${hue} 24% 20%)">${glasses}<path d="M35 46q5 4 10 0" fill="none" stroke-width="1.5" stroke-linecap="round"/></g>
    <g fill="hsl(${hue} 24% 20%)"><circle cx="33" cy="38" r="1.3"/><circle cx="47" cy="38" r="1.3"/></g>
  </svg></span>`;
}
