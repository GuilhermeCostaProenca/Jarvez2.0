import { type Attributes } from '../../Sheet';
import { Race } from '../Race';
import { type RaceAbility } from '../RaceAbility';
import { RaceName } from '../RaceName';
import { type SerializedDahllan } from '../SerializedRace';
export declare class Dahllan extends Race<SerializedDahllan> {
    static attributeModifiers: Partial<Attributes>;
    static readonly raceName = RaceName.dahllan;
    attributeModifiers: Partial<Attributes>;
    abilities: Record<string, RaceAbility>;
    constructor();
    protected serializeSpecific(): SerializedDahllan;
}
