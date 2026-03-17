import { type RaceName } from './RaceName';
import { type RaceStatic } from './RaceStatic';
export declare class Races {
    static map: Record<RaceName, RaceStatic>;
    static getAll(): RaceStatic[];
    static getByName(name: RaceName): RaceStatic;
}
