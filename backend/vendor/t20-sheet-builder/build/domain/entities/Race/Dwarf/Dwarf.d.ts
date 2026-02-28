import type { Attributes } from '../../Sheet/Attributes';
import { Race } from '../Race';
import type { RaceAbility } from '../RaceAbility';
import { RaceName } from '../RaceName';
import { type SerializedDwarf } from '../SerializedRace';
export declare class Dwarf extends Race<SerializedDwarf> {
    static readonly raceName = RaceName.dwarf;
    static attributeModifiers: Partial<Attributes>;
    readonly abilities: Record<string, RaceAbility>;
    readonly attributeModifiers: Partial<Attributes>;
    constructor();
    protected serializeSpecific(): SerializedDwarf;
}
