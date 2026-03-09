import { WeaponPurposeRangedShooting } from '../../WeaponPurpose';
import { OffensiveWeapon } from '../OffensiveWeapon';
import { type FireArmWeaponName } from './FireArmWeaponName';
export declare abstract class FireArmWeapon extends OffensiveWeapon<FireArmWeaponName> {
    static purposes: WeaponPurposeRangedShooting[];
    readonly purposes: WeaponPurposeRangedShooting[];
    abstract name: FireArmWeaponName;
    constructor();
}
