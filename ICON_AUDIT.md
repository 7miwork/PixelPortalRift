# Icon Audit – IconLibrary vs ITEM_PROPERTIES

## Summary
- ITEM_PROPERTIES entries: 72
- BLOCK_PROPERTIES entries: 39
- Items present in both (block path in IconLibrary): 22

## Classification of procedural item icons (`create_item_texture`)
- Dedicated drawing branch: 34 items (tools, gems, keys, food, special)
- Block-color fallback (item is also a block): 21 items
- **Gray fallback (no dedicated icon, not a block): 17 items** ← candidates for improvement

### Gray-fallback items (show as plain gray square in hotbar/inventory)
coal, iron_ingot, gold_ingot, stick, cooked_fish, gravel, torch, pearl,
crystal_shard, ruby, emerald, diamond, anchor_piece, slime_ball,
rotten_flesh, shark_tooth, radiation_suit

## IconLibrary.get resolution order
1. `assets/custom_blocks/<name>/` (user image) – highest priority
2. `assets/blocks/<name>.png` if name in BLOCK_PROPERTIES
3. `BLOCK_PROPERTIES[name].color` if no PNG
4. `asset_loader` procedural item texture otherwise
5. Neutral gray `(0.6,0.6,0.6)` if nothing else

## Findings / recommendations
- The 17 gray-fallback items lack a dedicated procedural drawing and are not blocks, so they render as gray squares unless an `assets/items/<name>.png` exists.
- Suggested fixes: add small dedicated `elif` branches in `create_item_texture` for the most visible ones (coal, stick, torch, pearl, diamond, ruby, emerald, cooked_fish), or reuse block colors where applicable (gravel, torch).
- Items that are both block & item (e.g. gravel, torch, wood, cobblestone) already fall back to their block color, which is acceptable but could be unified.
- No item currently resolves to the final neutral gray in IconLibrary, because `create_item_texture` always returns a surface; the gray path in IconLibrary is effectively dead for items but still reachable for unknown names.

## Action items
- [ ] Add procedural icons for the 17 gray items (or PNGs under assets/items/).
- [ ] Optionally unify block-items so they reuse block PNG/color consistently.
- [ ] Keep custom_blocks override as highest priority (verified by smoke tests).
