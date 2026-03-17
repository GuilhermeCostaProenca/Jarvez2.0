import { type Attributes } from '../../Sheet';
import { Race } from '../Race';
import { type RaceAbility } from '../RaceAbility';
import { RaceName } from '../RaceName';
import { type SerializedGoblin } from '../SerializedRace';
export declare class Goblin extends Race<SerializedGoblin> {
    static readonly raceName = RaceName.goblin;
    static attributeModifiers: Partial<Attributes>;
    static abilities: Record<string, RaceAbility>;
    attributeModifiers: Partial<Attributes>;
    abilities: Record<string, RaceAbility>;
    constructor();
    protected serializeSpecific(): SerializedGoblin;
}
