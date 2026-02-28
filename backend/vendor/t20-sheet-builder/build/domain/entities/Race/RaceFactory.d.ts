import { type RaceInterface } from './RaceInterface';
import { type SerializedRace } from './SerializedRace';
export declare class RaceFactory {
    static makeFromSerialized(serializedRace: SerializedRace): RaceInterface;
    private static makeHuman;
    private static makeMinotaur;
    private static makeQareen;
    private static makeElf;
    private static makeGoblin;
    private static makeDwarf;
    private static makeDahllan;
    private static makeLefeu;
}
