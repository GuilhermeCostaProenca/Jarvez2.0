import { type RaceInterface } from '../../Race';
import { type SheetRaceInterface } from '../SheetRaceInterface';
export declare class CharacterSheetRace implements SheetRaceInterface {
    private readonly race;
    constructor(race: RaceInterface);
    getRace(): RaceInterface;
}
