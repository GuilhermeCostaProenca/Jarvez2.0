import { type ExoticWeaponName } from './ExoticWeaponName';
import { type ExoticWeaponStatic } from './ExoticWeaponStatic';
export declare class ExoticWeapons {
    static map: Record<ExoticWeaponName, ExoticWeaponStatic>;
    static getAll(): ExoticWeaponStatic[];
    static getByName(name: ExoticWeaponName): ExoticWeaponStatic;
}
