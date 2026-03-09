import { type TriggeredEffectName } from '../Ability';
import { type TriggeredEffectActivation } from '../Ability/TriggeredEffectActivation';
import type { Attack, SerializedAttack } from '../Attack/Attack';
import { type Context } from '../Context';
import { type RollResult } from '../Dice/RollResult';
import { type OffensiveWeapon } from '../Inventory/Equipment/Weapon/OffensiveWeapon/OffensiveWeapon';
import { ManaCost, type SerializedManaCost } from '../ManaCost';
import { type TriggeredEffectMap } from '../Map';
import { type Modifiers, type ModifiersMaxTotalCalculators, type ModifiersTotalCalculators, type SerializedModifiers } from '../Modifier/Modifiers';
import { type RandomInterface } from '../Random';
import { type Attribute, type Attributes } from '../Sheet';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { type SkillName } from '../Skill';
import { type SheetSkill, type SheetSkillsObject } from '../Skill/SheetSkill';
import { CharacterAttackTriggeredEffect, type SerializedCharacterAttackTriggeredEffect } from './CharacterAttackTriggeredEffect';
import { CharacterAttackModifiers } from './CharactterAttackModifiers';
export type AttackResult = {
    damage: {
        total: number;
        modifiers: Modifiers;
        rollResult: RollResult;
        modifiersTotal: number;
    };
    test: {
        total: number;
        modifiers: Modifiers;
        rollResult: RollResult;
        modifiersTotal: number;
    };
    isCritical: boolean;
    isFumble: boolean;
};
export type SerializedCharacterAttack = {
    attack: SerializedAttack;
    modifiers: {
        test: SerializedModifiers;
        damage: SerializedModifiers;
    };
    defaultSkill: SkillName;
    testSkillAttributeModifier: number;
    manaCost: SerializedManaCost;
    triggeredEffects: SerializedCharacterAttackTriggeredEffect[];
};
type CharacterAttackConstructorParams = {
    modifiers?: Partial<CharacterAttackModifiers>;
    attributes: Attributes;
    maxTotalCalculators: ModifiersMaxTotalCalculators;
    skills: SheetSkillsObject;
    weapon: OffensiveWeapon;
    totalCalculators: ModifiersTotalCalculators;
    triggeredEffects: TriggeredEffectMap;
};
export declare class CharacterAttack {
    readonly modifiers: CharacterAttackModifiers;
    readonly attack: Attack;
    private readonly damageAttributeModifierIndex;
    private readonly maxTotalCalculators;
    private readonly totalCalculators;
    private readonly attributes;
    private readonly skills;
    private readonly triggeredEffects;
    constructor(params: CharacterAttackConstructorParams);
    changeTestAttackAttribute(attribute: Attribute): void;
    getDefaultTestSkill(): SheetSkill;
    roll(random?: RandomInterface): AttackResult;
    enableTriggeredEffect(activation: TriggeredEffectActivation): void;
    disableTriggeredEffect(effectName: TriggeredEffectName): void;
    getTestModifiersMaxTotal(): number;
    getTestModifiersTotal(): number;
    getDamageModifiersMaxTotal(): number;
    getDamageModifiersTotal(): number;
    getTriggeredEffects(): Map<TriggeredEffectName, CharacterAttackTriggeredEffect>;
    getManaCost(): ManaCost;
    getTestSkillAttributeModifier(): number;
    serialize(sheet: SheetInterface, context: Context): SerializedCharacterAttack;
    private addDamageAttributeFixedModifier;
}
export {};
