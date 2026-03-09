export declare class Powers {
    static readonly map: {
        shell: typeof import("./GeneralPower").Shell;
        emptyMind: import("./GrantedPower/GrantedPowerStatic").GrantedPowerStatic;
        analyticMind: import("./GrantedPower/GrantedPowerStatic").GrantedPowerStatic;
        linWuTradition: import("./GrantedPower/GrantedPowerStatic").GrantedPowerStatic;
        dodge: import("./GeneralPower/GeneralPowerStatic").GeneralPowerStatic;
        oneWeaponStyle: import("./GeneralPower/GeneralPowerStatic").GeneralPowerStatic;
        medicine: import("./GeneralPower/GeneralPowerStatic").GeneralPowerStatic;
        ironWill: import("./GeneralPower/GeneralPowerStatic").GeneralPowerStatic;
    };
    getAll(): (typeof import("./GeneralPower").Shell | import("./GrantedPower/GrantedPowerStatic").GrantedPowerStatic | import("./GeneralPower/GeneralPowerStatic").GeneralPowerStatic)[];
}
