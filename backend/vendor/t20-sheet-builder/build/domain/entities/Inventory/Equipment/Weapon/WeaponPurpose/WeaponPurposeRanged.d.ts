import { WeaponPurpose, type WeaponPurposeParams } from './WeaponPurpose';
export type WeaponPurposeRangedParams = Omit<WeaponPurposeParams, 'defaultSkill'>;
export declare abstract class WeaponPurposeRanged extends WeaponPurpose {
    constructor(params: WeaponPurposeRangedParams);
}
