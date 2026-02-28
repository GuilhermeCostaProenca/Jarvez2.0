import type { ArmorStatic } from '../ArmorStatic';
import { type LightArmorName } from './LightArmorName';
import { type LightArmorStatic } from './LightArmorStatic';
export declare class LightArmors {
    static map: Record<LightArmorName, LightArmorStatic>;
    static getAll(): ArmorStatic[];
    static get(name: LightArmorName): LightArmorStatic;
}
