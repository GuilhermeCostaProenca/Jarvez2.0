import { type HeavyArmorName } from './HeavyArmorName';
import { type HeavyArmorStatic } from './HeavyArmorStatic';
export declare class HeavyArmors {
    static map: Record<HeavyArmorName, HeavyArmorStatic>;
    static getAll(): HeavyArmorStatic[];
    static get(name: HeavyArmorName): HeavyArmorStatic;
}
