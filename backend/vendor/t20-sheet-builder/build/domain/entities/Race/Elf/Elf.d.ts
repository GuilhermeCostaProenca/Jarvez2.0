import { type Attributes } from '../../Sheet';
import { Race } from '../Race';
import { type RaceAbility } from '../RaceAbility';
import { RaceName } from '../RaceName';
import { type SerializedElf } from '../SerializedRace';
export declare class Elf extends Race<SerializedElf> {
    static attributeModifiers: Partial<Attributes>;
    static readonly raceName = RaceName.elf;
    attributeModifiers: Partial<Attributes>;
    abilities: Record<string, RaceAbility>;
    constructor();
    protected serializeSpecific(): SerializedElf;
}
