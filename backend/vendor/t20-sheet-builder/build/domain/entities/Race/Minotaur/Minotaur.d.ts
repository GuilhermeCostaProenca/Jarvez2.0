import { type Attributes } from '../../Sheet';
import { Race } from '../Race';
import { type RaceAbility } from '../RaceAbility';
import { RaceName } from '../RaceName';
import { type SerializedMinotaur } from '../SerializedRace';
export declare class Minotaur extends Race<SerializedMinotaur> {
    static attributeModifiers: Partial<Attributes>;
    static readonly raceName = RaceName.minotaur;
    attributeModifiers: Partial<Attributes>;
    abilities: Record<string, RaceAbility>;
    constructor();
    protected serializeSpecific(): SerializedMinotaur;
}
