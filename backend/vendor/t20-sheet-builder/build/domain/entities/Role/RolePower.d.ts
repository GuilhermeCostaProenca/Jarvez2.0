import type { PowerInterface } from '../Power/Power';
import { Power } from '../Power/Power';
import { type SerializedSheetRolePower } from '../Sheet/SerializedSheet/SerializedSheetInterface';
import type { RolePowerName } from './RolePowerName';
export type RolePowerInterface = PowerInterface & {
    name: RolePowerName;
    serialize(): SerializedSheetRolePower;
};
export declare abstract class RolePower extends Power implements RolePowerInterface {
    readonly name: RolePowerName;
    constructor(name: RolePowerName);
    serialize(): SerializedSheetRolePower;
}
