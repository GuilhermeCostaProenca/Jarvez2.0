import { type Context } from '../Context';
import { type SerializedSheetContextualModifiersList, type SerializedSheetModifiersList, type SerializedSheetPerLevelModifiersList } from '../Sheet';
import { type Attributes } from '../Sheet/Attributes';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { ContextualModifiersList, type ContextualModifiersListTotalCalculator } from './ContextualModifier';
import { FixedModifiersList, type FixedModifiersListTotalCalculator } from './FixedModifier';
import { PerLevelModifiersList, type PerLevelModifiersListTotalCalculator } from './PerLevelModifier';
export type ModifiersParams = {
    fixed: FixedModifiersList;
    contextual: ContextualModifiersList;
    perLevel: PerLevelModifiersList;
};
export type ModifiersTotalCalculators = {
    fixedCalculator: FixedModifiersListTotalCalculator;
    contextCalculator: ContextualModifiersListTotalCalculator;
    perLevelCalculator: PerLevelModifiersListTotalCalculator;
};
export type ModifiersMaxTotalCalculators = Omit<ModifiersTotalCalculators, 'contextCalculator'>;
export type SerializedModifiers = {
    fixed: SerializedSheetModifiersList;
    contextual: SerializedSheetContextualModifiersList;
    perLevel: SerializedSheetPerLevelModifiersList;
};
export declare class Modifiers {
    readonly fixed: FixedModifiersList;
    readonly contextual: ContextualModifiersList;
    readonly perLevel: PerLevelModifiersList;
    constructor(params?: Partial<ModifiersParams>);
    clone(): Modifiers;
    getTotal({ contextCalculator, fixedCalculator, perLevelCalculator, }: ModifiersTotalCalculators): number;
    getMaxTotal(attributes: Attributes, { fixedCalculator, perLevelCalculator, }: ModifiersMaxTotalCalculators): number;
    serialize(sheet: SheetInterface, context: Context): SerializedModifiers;
}
