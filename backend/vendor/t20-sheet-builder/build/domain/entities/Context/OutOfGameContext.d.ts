import { type Location } from '../Sheet';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { Context } from './Context';
export declare class OutOfGameContext extends Context {
    sheet: SheetInterface | undefined;
    activateContextualModifiers: boolean;
    getCurrentLocation(): Location | undefined;
}
