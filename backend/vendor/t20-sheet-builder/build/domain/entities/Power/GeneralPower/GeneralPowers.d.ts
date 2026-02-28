import { type GeneralPowerName } from './GeneralPowerName';
import { type GeneralPowerStatic } from './GeneralPowerStatic';
export declare class GeneralPowers {
    static readonly map: Record<GeneralPowerName, GeneralPowerStatic>;
    static getAll(): GeneralPowerStatic[];
}
