import { type Location } from '../Sheet';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { Context } from './Context';
export declare class PreviewContext extends Context {
    sheet: SheetInterface;
    activateContextualModifiers: boolean;
    constructor(sheet: SheetInterface);
    getCurrentLocation(): Location | undefined;
}
