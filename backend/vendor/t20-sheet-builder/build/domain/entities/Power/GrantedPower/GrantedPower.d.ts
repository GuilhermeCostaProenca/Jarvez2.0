import { type SerializedSheetGrantedPower } from '../../Sheet';
import { Power } from '../Power';
import { type GrantedPowerName } from './GrantedPowerName';
export declare abstract class GrantedPower extends Power {
    name: GrantedPowerName;
    constructor(name: GrantedPowerName);
    serialize(): SerializedSheetGrantedPower;
}
