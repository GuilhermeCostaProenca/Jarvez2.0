import { type SerializedOriginPower, type SerializedOriginPowers } from '../../Origin/OriginBenefit/SerializedOriginBenefit';
import type { OriginName } from '../../Origin/OriginName';
import type { PowerInterface } from '../Power';
import { Power } from '../Power';
import { type OriginPowerName } from './OriginPowerName';
export type OriginPowerInterface<S extends SerializedOriginPowers = SerializedOriginPowers> = PowerInterface & {
    source: OriginName;
    name: OriginPowerName;
    serialize(): SerializedOriginPower<S>;
};
export declare abstract class OriginPower<S extends SerializedOriginPowers = SerializedOriginPowers> extends Power implements OriginPowerInterface<S> {
    readonly name: OriginPowerName;
    abstract source: OriginName;
    constructor(name: OriginPowerName);
    abstract serialize(): SerializedOriginPower<S>;
}
