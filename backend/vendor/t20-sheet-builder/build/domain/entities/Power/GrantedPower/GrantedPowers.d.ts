import { type GrantedPowerName } from './GrantedPowerName';
import { type GrantedPowerStatic } from './GrantedPowerStatic';
export declare class GrantedPowers {
    static readonly map: Record<GrantedPowerName, GrantedPowerStatic>;
    static getAll(): GrantedPowerStatic[];
}
