import { type ContextInterface } from '../../Context/ContextInterface';
import { type SheetInterface } from '../SheetInterface';
import { type SerializedSheetInterface } from './SerializedSheetInterface';
/**
* @deprecated Use `sheet.serialize()` instead
*/
export declare class SheetSerializer {
    private readonly context;
    constructor(context: ContextInterface);
    serialize(sheet: SheetInterface): SerializedSheetInterface;
}
