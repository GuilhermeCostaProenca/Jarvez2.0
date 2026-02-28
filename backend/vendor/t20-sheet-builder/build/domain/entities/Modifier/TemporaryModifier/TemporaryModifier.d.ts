import type { EffectDuration } from '../../Ability/ActivateableAbilityEffect';
import type { TranslatableName } from '../../Translator';
import { Modifier } from '../Modifier';
import type { TemporaryModifierInterface } from './TemporaryModifierInterface';
export declare class TemporaryModifier extends Modifier implements TemporaryModifierInterface {
    readonly duration: EffectDuration;
    constructor(source: TranslatableName, value: number, duration: EffectDuration);
}
