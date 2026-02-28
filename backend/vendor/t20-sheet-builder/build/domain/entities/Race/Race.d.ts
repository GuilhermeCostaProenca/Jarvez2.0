import type { Attributes } from '../Sheet/Attributes';
import { type TransactionInterface } from '../Sheet/TransactionInterface';
import type { RaceAbility } from './RaceAbility';
import type { RaceInterface } from './RaceInterface';
import type { RaceName } from './RaceName';
import { type SerializedRace, type SerializedRaceBasic, type SerializedRaces } from './SerializedRace';
export declare abstract class Race<S extends SerializedRaces = SerializedRaces> implements RaceInterface<S> {
    readonly name: RaceName;
    static serialize(race: Race): SerializedRaceBasic;
    abstract readonly attributeModifiers: Partial<Attributes>;
    abstract readonly abilities: Record<string, RaceAbility>;
    constructor(name: RaceName);
    addToSheet(transaction: TransactionInterface): void;
    serialize(): SerializedRace<S>;
    protected abstract serializeSpecific(): S;
    private applyAttributesModifiers;
    private applyAbilities;
}
