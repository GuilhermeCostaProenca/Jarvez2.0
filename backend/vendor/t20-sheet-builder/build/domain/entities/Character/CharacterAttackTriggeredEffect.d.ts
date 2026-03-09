import { type SerializedTriggeredEffect, type TriggeredEffect, type TriggeredEffectModifiers } from '../Ability';
import { type TriggeredEffectActivation } from '../Ability/TriggeredEffectActivation';
import { type Context } from '../Context';
import { type ManaCost } from '../ManaCost';
import { type SerializedModifiers } from '../Modifier';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { type CharacterModifierName } from './CharacterModifiers';
import { type CharacterAttackModifiers } from './CharactterAttackModifiers';
export type EnabledEffectModifiersIndexes = Partial<Record<CharacterModifierName, number>>;
export type SerializedCharacterAttackTriggeredEffect = {
    effect: SerializedTriggeredEffect;
    modifiers: Partial<Record<CharacterModifierName, SerializedModifiers>>;
};
export declare class CharacterAttackTriggeredEffect {
    readonly effect: TriggeredEffect;
    readonly modifiersIndexes: EnabledEffectModifiersIndexes;
    readonly modifiers: TriggeredEffectModifiers;
    private isEnabled;
    private manaCost?;
    constructor(effect: TriggeredEffect, modifiers: CharacterAttackModifiers);
    enable(activation: TriggeredEffectActivation): void;
    disable(): void;
    getIsEnabled(): boolean;
    getManaCost(): ManaCost | undefined;
    serialize(sheet: SheetInterface, context: Context): SerializedCharacterAttackTriggeredEffect;
}
