import { type ActivateableAbilityEffect } from '../Ability';
import { type TranslatableName } from '../Translator';
export declare class SheetActivateableEffects {
    private readonly effects;
    register(effect: ActivateableAbilityEffect): void;
    getEffects(): Map<TranslatableName, ActivateableAbilityEffect>;
    getEffect(source: TranslatableName): ActivateableAbilityEffect | undefined;
}
