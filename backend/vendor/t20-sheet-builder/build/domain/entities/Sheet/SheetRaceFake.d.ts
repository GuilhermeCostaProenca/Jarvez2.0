import { type RaceInterface } from '../Race';
import { type SheetRaceInterface } from './SheetRaceInterface';
export declare class SheetRaceFake implements SheetRaceInterface {
    race: RaceInterface | undefined;
    chooseRace: import("vitest").Mock<any, any>;
    constructor(race?: RaceInterface | undefined);
    getRace(): RaceInterface | undefined;
}
