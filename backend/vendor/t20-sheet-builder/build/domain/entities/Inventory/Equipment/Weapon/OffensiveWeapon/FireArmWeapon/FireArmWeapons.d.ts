import { type FireArmWeaponName } from './FireArmWeaponName';
import { type FireArmWeaponStatic } from './FireArmWeaponStatic';
export declare class FireArmWeapons {
    static map: Record<FireArmWeaponName, FireArmWeaponStatic>;
    static getAll(): FireArmWeaponStatic[];
    static getByName(name: FireArmWeaponName): FireArmWeaponStatic;
}
