import { type ContextInterface, type TranslatableName } from '..';
import { Resistance } from '../Resistance/Resistance';
import { type ResistanceName } from '../Resistance/ResistanceName';
import { type Attributes } from './Attributes';
import { type SheetInterface } from './SheetInterface';
import { type SerializedSheetResistencies, type SheetResistencesInterface } from './SheetResistencesInterface';
export type SheetResistenciesType = Record<ResistanceName, Resistance>;
export declare class SheetResistences implements SheetResistencesInterface {
    private resistances;
    addResistance(resistance: ResistanceName, value: number, source: TranslatableName): void;
    getTotal(resistance: ResistanceName, attributes: Attributes): number;
    getResistances(): Partial<SheetResistenciesType>;
    serialize(sheet: SheetInterface, context: ContextInterface): SerializedSheetResistencies;
}
