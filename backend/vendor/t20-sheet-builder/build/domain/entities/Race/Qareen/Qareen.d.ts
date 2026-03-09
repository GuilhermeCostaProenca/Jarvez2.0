import { type Attributes } from '../../Sheet';
import { type SpellName } from '../../Spell';
import { Race } from '../Race';
import { RaceName } from '../RaceName';
import { type SerializedQareen } from '../SerializedRace';
import { Desires } from './Desires/Desires';
import { ElementalResistance } from './ElementalResistance/ElementalResistance';
import { MysticTattoo } from './MysticTattoo/MysticTattoo';
import { type QareenType } from './QareenType';
export declare class Qareen extends Race<SerializedQareen> {
    readonly qareenType: QareenType;
    static attributeModifiers: Partial<Attributes>;
    static readonly raceName = RaceName.qareen;
    attributeModifiers: Partial<Attributes>;
    abilities: {
        desires: Desires;
        elementalResistance: ElementalResistance;
        mysticTattoo: MysticTattoo;
    };
    constructor(qareenType: QareenType, mysticTattooSpell: SpellName);
    protected serializeSpecific(): SerializedQareen;
}
