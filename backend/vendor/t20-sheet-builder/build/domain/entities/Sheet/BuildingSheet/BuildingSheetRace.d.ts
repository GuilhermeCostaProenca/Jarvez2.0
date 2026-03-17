import { type RaceInterface } from '../../Race';
import { type SheetRaceInterface } from '../SheetRaceInterface';
import { type TransactionInterface } from '../TransactionInterface';
export declare class BuildingSheetRace implements SheetRaceInterface {
    private race;
    constructor(race?: RaceInterface | undefined);
    chooseRace(race: RaceInterface, transaction: TransactionInterface): void;
    getRace(): RaceInterface | undefined;
}
