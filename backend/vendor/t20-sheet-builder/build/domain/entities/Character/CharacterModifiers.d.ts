import { type Context } from '../Context';
import { Modifiers, type SerializedModifiers } from '../Modifier/Modifiers';
import { type SheetInterface } from '../Sheet/SheetInterface';
export declare enum CharacterModifierName {
    attack = "attack",
    damage = "damage",
    defense = "defense",
    armorPenalty = "armorPenalty",
    skillExceptAttack = "skillExceptAttack",
    skill = "skill"
}
export type SerializedCharacterModifiers = Record<CharacterModifierName, SerializedModifiers>;
export declare class CharacterModifiers {
    readonly attack: Modifiers;
    readonly damage: Modifiers;
    readonly defense: Modifiers;
    readonly armorPenalty: Modifiers;
    readonly skillExceptAttack: Modifiers;
    readonly skill: Modifiers;
    serialize(sheet: SheetInterface, context: Context): SerializedCharacterModifiers;
}
