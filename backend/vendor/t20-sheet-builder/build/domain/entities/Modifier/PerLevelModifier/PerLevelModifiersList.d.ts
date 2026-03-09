import { type ContextInterface } from '../../Context';
import { Level } from '../../Sheet/Level';
import { type SerializedSheetPerLevelModifiersList } from '../../Sheet/SerializedSheet/SerializedSheetInterface';
import { type SheetInterface } from '../../Sheet/SheetInterface';
import { ModifiersList } from '../ModifiersList';
import type { ModifiersListInterface } from '../ModifiersListInterface';
import type { PerLevelModifierInterface } from './PerLevelModifierInterface';
export type PerLevelModifiersListInterface = Omit<ModifiersListInterface<PerLevelModifierInterface>, 'serialize'> & {
    getTotalPerLevel(level: Level): number;
    serialize(sheet: SheetInterface, context: ContextInterface): SerializedSheetPerLevelModifiersList;
};
export declare class PerLevelModifiersList extends ModifiersList<PerLevelModifierInterface> implements PerLevelModifiersListInterface {
    serialize(sheet: SheetInterface, context: ContextInterface): SerializedSheetPerLevelModifiersList;
    getTotalPerLevel(level: Level): number;
}
