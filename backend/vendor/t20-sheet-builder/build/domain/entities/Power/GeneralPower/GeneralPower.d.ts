import { type SerializedSheetGeneralPower } from '../../Sheet/SerializedSheet/SerializedSheetInterface';
import type { PowerInterface } from '../Power';
import { Power } from '../Power';
import { type GeneralPowerGroup } from './GeneralPowerGroup';
import type { GeneralPowerName } from './GeneralPowerName';
export type GeneralPowerInterface = PowerInterface & {
    name: GeneralPowerName;
    group: GeneralPowerGroup;
    serialize(): SerializedSheetGeneralPower;
};
export declare abstract class GeneralPower extends Power implements GeneralPowerInterface {
    readonly name: GeneralPowerName;
    abstract group: GeneralPowerGroup;
    constructor(name: GeneralPowerName);
    serialize(): SerializedSheetGeneralPower;
}
