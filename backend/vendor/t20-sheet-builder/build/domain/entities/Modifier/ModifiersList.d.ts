import { type TranslatableName } from '..';
import { type ContextInterface } from '../Context';
import { type SerializedSheetModifiersList } from '../Sheet/SerializedSheet/SerializedSheetInterface';
import { type SheetInterface } from '../Sheet/SheetInterface';
import type { ModifierInterface } from './ModifierInterface';
import type { ModifiersListInterface, ModifiersListTotalCalculator } from './ModifiersListInterface';
export declare abstract class ModifiersList<T extends ModifierInterface> implements ModifiersListInterface<T> {
    modifiers: T[];
    getTotal(totalCalculator: ModifiersListTotalCalculator<T>): number;
    add(...modifier: T[]): number;
    append(modifiersList: ModifiersList<T>): void;
    remove(index: number): void;
    get(source: TranslatableName): T | undefined;
    clone(): ModifiersList<T>;
    abstract serialize(sheet: SheetInterface, context: ContextInterface): SerializedSheetModifiersList;
}
