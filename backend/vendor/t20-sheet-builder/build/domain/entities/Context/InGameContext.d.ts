import type { Location } from '../Sheet/CharacterSheet/CharacterSheetInterface';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { Context } from './Context';
export declare class InGameContext extends Context {
    readonly sheet: SheetInterface;
    activateContextualModifiers: boolean;
    private readonly location;
    constructor(initialLocation: Location, sheet: SheetInterface);
    getCurrentLocation(): Location;
}
