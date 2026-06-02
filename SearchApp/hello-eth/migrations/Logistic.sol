pragma solidity >= 0.8.11 <= 0.8.11;
pragma experimental ABIEncoderV2;
//evault solidity code
contract Logistic {

    uint public userCount = 0; 
    mapping(uint => user) public userList; 
     struct user
     {
       string username;
       string password;
       string phone;
       string email;
       string home_address;      
     }
 
   // events 
   event userCreated(uint indexed _userId);
   
   //function  to save user details to Blockchain
   function saveUser(string memory uname, string memory pass, string memory phone, string memory emailid, string memory homes_address) public {
      userList[userCount] = user(uname, pass, phone, emailid, homes_address);
      emit userCreated(userCount);
      userCount++;
    }

     //get user count
    function getUserCount()  public view returns (uint) {
          return  userCount;
    }

    uint public trapCount = 0; 
    mapping(uint => trap) public trapList; 
     struct trap
     {
       string username;
       string filename;
       string trapdoor;      
       string date;
       string hashcode;
     }
 
   // events 
   event trapCreated(uint indexed _ehrId);
   
   //function  to save trapdoor details to Blockchain
   function saveTrapdoor(string memory uname, string memory fname, string memory td, string memory dd, string memory hc) public {
      trapList[trapCount] = trap(uname, fname, td, dd, hc);
      emit trapCreated(trapCount);
      trapCount++;
    }

    //get trap count
    function getTrapCount()  public view returns (uint) {
          return trapCount;
    }

   function getUsername(uint i) public view returns (string memory) {
        user memory usr = userList[i];
	return usr.username;
    }

    function getPassword(uint i) public view returns (string memory) {
        user memory usr = userList[i];
	return usr.password;
    }

    function getPhone(uint i) public view returns (string memory) {
        user memory usr = userList[i];
	return usr.phone;
    }

   
    function getEmail(uint i) public view returns (string memory) {
        user memory usr = userList[i];
	return usr.email;
    }

    function getAddress(uint i) public view returns (string memory) {
        user memory usr = userList[i];
	return usr.home_address;
    }

     function getHashcode(uint i) public view returns (string memory) {
        trap memory tl = trapList[i];
	return tl.hashcode;
    }

    function getOwner(uint i) public view returns (string memory) {
        trap memory tl = trapList[i];
	return tl.username;
    }

    function getFilename(uint i) public view returns (string memory) {
        trap memory tl = trapList[i];
	return tl.filename;
    }

    function getTrapdoor(uint i) public view returns (string memory) {
        trap memory tl = trapList[i];
	return tl.trapdoor;
    }

    function getDate(uint i) public view returns (string memory) {
        trap memory tl = trapList[i];
	return tl.date;
    }    
}