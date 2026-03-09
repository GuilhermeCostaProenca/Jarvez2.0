import { type OriginPowerName } from './OriginPowerName';
import { type OriginPowerStatic } from './OriginPowerStatic';
export declare class OriginPowers {
    static readonly map: Record<OriginPowerName, OriginPowerStatic>;
    static getAll(): OriginPowerStatic[];
}
