import type { Location } from '../Sheet/CharacterSheet/CharacterSheetInterface';
import { type SheetInterface } from '../Sheet/SheetInterface';
import { Context } from './Context';
export declare class InGameContextFake extends Context {
    sheet: SheetInterface | undefined;
    activateContextualModifiers: boolean;
    location: Location;
    getCurrentLocation(): Location;
}
