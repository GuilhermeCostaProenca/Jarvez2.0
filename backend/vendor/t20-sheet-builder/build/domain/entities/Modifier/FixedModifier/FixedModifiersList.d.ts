import { type ContextInterface } from '../../Context';
import { type SerializedSheetModifiersList } from '../../Sheet/SerializedSheet/SerializedSheetInterface';
import { type SheetInterface } from '../../Sheet/SheetInterface';
import { ModifiersList } from '../ModifiersList';
import type { ModifiersListInterface } from '../ModifiersListInterface';
import type { FixedModifierInterface } from './FixedModifier';
export type FixedModifiersListInterface = ModifiersListInterface<FixedModifierInterface>;
export declare class FixedModifiersList extends ModifiersList<FixedModifierInterface> implements ModifiersListInterface<FixedModifierInterface> {
    serialize(sheet: SheetInterface, _context: ContextInterface): SerializedSheetModifiersList;
}
