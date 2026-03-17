import { type SerializedTriggeredEffect, type TriggerEvent, type TriggeredEffect, type TriggeredEffectModifiers } from '../Ability';
import { type TriggeredEffectActivation } from '../Ability/TriggeredEffectActivation';
import { type Context } from '../Context';
import { type ManaCost } from '../ManaCost';
import { type Modifiers, type SerializedModifiers } from '../Modifier';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { type CharacterModifierName } from './CharacterModifiers';
export type EnabledEffectModifiersIndexes = Partial<Record<TriggerEvent, number>>;
export type SerializedCharacterAttackTriggeredEffect = {
    effect: SerializedTriggeredEffect;
    modifiers: Partial<Record<CharacterModifierName, SerializedModifiers>>;
};
export declare class CharacterDefenseTriggeredEffect {
    readonly effect: TriggeredEffect;
    readonly modifiersIndexes: EnabledEffectModifiersIndexes;
    readonly modifiers: TriggeredEffectModifiers;
    private isEnabled;
    private manaCost?;
    constructor(effect: TriggeredEffect, defenseModifiers: Modifiers);
    enable(activation: TriggeredEffectActivation): void;
    disable(): void;
    getIsEnabled(): boolean;
    getManaCost(): ManaCost | undefined;
    serialize(sheet: SheetInterface, context: Context): SerializedCharacterAttackTriggeredEffect;
}
