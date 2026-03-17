import { type SerializedSheetModifiersList, type ContextInterface, type TranslatableName } from '..';
import { type Attributes } from '../Sheet/Attributes';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { type ResistanceName } from './ResistanceName';
export type SerializedResistance = {
    resisted: ResistanceName;
    fixedModifiers: SerializedSheetModifiersList;
    source: TranslatableName;
};
export declare class Resistance {
    readonly source: TranslatableName;
    readonly resisted: ResistanceName;
    private readonly fixedModifiers;
    constructor(resistance: ResistanceName, value: number, source: TranslatableName);
    getTotal(attributes: Attributes): number;
    serialize(sheet: SheetInterface, context: ContextInterface): SerializedResistance;
}
