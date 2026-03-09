import type { Attribute } from '../../Sheet/Attributes';
import type { TranslatableName } from '../../Translator';
import type { ContextualModifierInterface } from './ContextualModifierInterface';
import type { ModifierCondition } from './ContextualModifiersListInterface';
import { Modifier } from '../Modifier';
type ContextualModifierParams = {
    source: TranslatableName;
    value: number;
    condition: ModifierCondition;
    attributeBonuses?: Set<Attribute>;
};
export declare class ContextualModifier extends Modifier implements ContextualModifierInterface {
    readonly condition: ModifierCondition;
    constructor(params: ContextualModifierParams);
}
export {};
